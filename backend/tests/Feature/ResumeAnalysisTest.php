<?php

namespace Tests\Feature;

use App\Models\Resume;
use App\Models\ResumeAnalysis;
use App\Models\User;
use App\Services\ResumeParserService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class ResumeAnalysisTest extends TestCase
{
    use RefreshDatabase;

    private function fakeAiEngine(
        array $overrides = []
    ): void {
        $response = array_replace([
            'ats_score' => 50,
            'extracted_name' => 'John Doe',
            'extracted_email' => 'john@example.com',
            'skills' => [
                'laravel',
                'angular',
            ],
            'education' => [
                'BSc Computer Science',
            ],
            'experience' => [
                'Software Engineer',
            ],
            'summary' => 'Mocked AI analysis summary.',
            'status' => 'completed',
        ], $overrides);

        Http::fake([
            config('services.ai_engine.url').'/analyze'
                => Http::response($response, 200),
        ]);
    }

    public function test_authenticated_user_can_analyze_resume(): void
    {
        $user = User::factory()->create();

        $resume = Resume::create([
            'user_id' => $user->id,
            'title' => 'Test Resume',
            'file_name' => 'resume.pdf',
            'file_path' => 'resumes/test/resume.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);

        $this->mock(
            ResumeParserService::class,
            function ($mock) {
                $mock->shouldReceive('extractText')
                    ->once()
                    ->withArgs(
                        fn ($resume) => $resume instanceof Resume
                    )
                    ->andReturn(
                        'John Doe Software Engineer Laravel Angular'
                    );
            }
        );

        $this->fakeAiEngine();

        $response = $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analyze"
            );

        $response
            ->assertStatus(201)
            ->assertJsonPath(
                'data.resume_id',
                $resume->id
            )
            ->assertJsonPath(
                'data.ats_score',
                50
            )
            ->assertJsonPath(
                'data.extracted_name',
                'John Doe'
            )
            ->assertJsonPath(
                'data.extracted_email',
                'john@example.com'
            )
            ->assertJsonPath(
                'data.status',
                'completed'
            );

        $this->assertDatabaseHas(
            'resume_analyses',
            [
                'resume_id' => $resume->id,
                'ats_score' => 50,
                'status' => 'completed',
                'summary' => 'Mocked AI analysis summary.',
            ]
        );

        Http::assertSent(function ($request) {
            return $request->url()
                === config('services.ai_engine.url').'/analyze'
                && $request->method() === 'POST'
                && $request['resume_text']
                    === 'John Doe Software Engineer Laravel Angular';
        });
    }

    public function test_reanalyzing_resume_does_not_create_duplicate_analysis(): void
    {
        $user = User::factory()->create();

        $resume = Resume::create([
            'user_id' => $user->id,
            'title' => 'Test Resume',
            'file_name' => 'resume.pdf',
            'file_path' => 'resumes/test/resume.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);

        $this->mock(
            ResumeParserService::class,
            function ($mock) {
                $mock->shouldReceive('extractText')
                    ->twice()
                    ->andReturn('Test resume content');
            }
        );

        $this->fakeAiEngine();

        $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analyze"
            )
            ->assertStatus(201);

        $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analyze"
            )
            ->assertStatus(201);

        $this->assertDatabaseCount(
            'resume_analyses',
            1
        );

        $this->assertDatabaseHas(
            'resume_analyses',
            [
                'resume_id' => $resume->id,
                'status' => 'completed',
            ]
        );
    }

    public function test_ai_engine_failure_marks_analysis_as_failed(): void
    {
        $user = User::factory()->create();

        $resume = Resume::create([
            'user_id' => $user->id,
            'title' => 'Test Resume',
            'file_name' => 'resume.pdf',
            'file_path' => 'resumes/test/resume.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);

        $this->mock(
            ResumeParserService::class,
            function ($mock) {
                $mock->shouldReceive('extractText')
                    ->once()
                    ->withArgs(
                        fn ($resume) => $resume instanceof Resume
                    )
                    ->andReturn('Test resume content');
            }
        );

        Http::fake([
            config('services.ai_engine.url').'/analyze'
                => Http::failedConnection(),
        ]);

        $response = $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analyze"
            );

        $response
            ->assertStatus(201)
            ->assertJsonPath(
                'data.resume_id',
                $resume->id
            )
            ->assertJsonPath(
                'data.status',
                'failed'
            )
            ->assertJsonPath(
                'data.ats_score',
                null
            );

        $analysis = ResumeAnalysis::where(
            'resume_id',
            $resume->id
        )->firstOrFail();

        $this->assertSame(
            'failed',
            $analysis->status
        );

        $this->assertNull(
            $analysis->ats_score
        );

        $this->assertNotEmpty(
            $analysis->summary
        );
    }

    public function test_real_pdf_resume_is_parsed_and_analyzed(): void
    {
        $user = User::factory()->create();

        $relativePath =
            'resumes/test/enterprise-test-resume.pdf';

        $sourcePath = base_path(
            'tests/fixtures/resumes/enterprise-test-resume.pdf'
        );

        $destinationPath = storage_path(
            'app/private/'.$relativePath
        );

        $this->assertFileExists($sourcePath);

        $directory = dirname($destinationPath);

        if (! is_dir($directory)) {
            mkdir(
                $directory,
                0755,
                true
            );
        }

        $this->assertTrue(
            copy(
                $sourcePath,
                $destinationPath
            )
        );

        try {
            $resume = Resume::create([
                'user_id' => $user->id,
                'title' => 'Enterprise PDF Test Resume',
                'file_name' => 'enterprise-test-resume.pdf',
                'file_path' => $relativePath,
                'file_type' => 'application/pdf',
                'file_size' => filesize($sourcePath),
                'status' => 'uploaded',
            ]);

            $this->fakeAiEngine([
                'ats_score' => 90,
                'extracted_email' => 'john.doe@example.com',
                'summary' => 'Real PDF integration test completed.',
            ]);

            $response = $this->actingAs($user)
                ->postJson(
                    "/api/v1/resumes/{$resume->id}/analyze"
                );

            $response
                ->assertStatus(201)
                ->assertJsonPath(
                    'data.resume_id',
                    $resume->id
                )
                ->assertJsonPath(
                    'data.ats_score',
                    90
                )
                ->assertJsonPath(
                    'data.extracted_name',
                    'John Doe'
                )
                ->assertJsonPath(
                    'data.extracted_email',
                    'john.doe@example.com'
                )
                ->assertJsonPath(
                    'data.status',
                    'completed'
                );

            $this->assertDatabaseHas(
                'resume_analyses',
                [
                    'resume_id' => $resume->id,
                    'ats_score' => 90,
                    'extracted_name' => 'John Doe',
                    'extracted_email' =>
                        'john.doe@example.com',
                    'status' => 'completed',
                ]
            );

            Http::assertSent(function ($request) {
                $text = $request['resume_text'] ?? '';

                return $request->url()
                    === config(
                        'services.ai_engine.url'
                    ).'/analyze'
                    && $request->method() === 'POST'
                    && str_contains(
                        $text,
                        'John Doe'
                    )
                    && str_contains(
                        $text,
                        'john.doe@example.com'
                    )
                    && str_contains(
                        $text,
                        'Python'
                    )
                    && str_contains(
                        $text,
                        'Laravel'
                    )
                    && str_contains(
                        $text,
                        'Angular'
                    )
                    && str_contains(
                        $text,
                        'Docker'
                    );
            });
        } finally {
            if (is_file($destinationPath)) {
                unlink($destinationPath);
            }
        }
    }

    public function test_authenticated_user_can_view_resume_analysis(): void
    {
        $user = User::factory()->create();

        $resume = Resume::create([
            'user_id' => $user->id,
            'title' => 'Test Resume',
            'file_name' => 'resume.pdf',
            'file_path' => 'resumes/test/resume.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);

        ResumeAnalysis::create([
            'resume_id' => $resume->id,
            'ats_score' => 85,
            'skills' => [
                'Laravel',
                'Angular',
            ],
            'summary' =>
                'Strong software engineering resume.',
            'status' => 'completed',
        ]);

        $response = $this->actingAs($user)
            ->getJson(
                "/api/v1/resumes/{$resume->id}/analysis"
            );

        $response
            ->assertStatus(200)
            ->assertJsonPath(
                'data.resume_id',
                $resume->id
            )
            ->assertJsonPath(
                'data.ats_score',
                85
            )
            ->assertJsonPath(
                'data.status',
                'completed'
            );
    }

    public function test_user_cannot_analyze_another_users_resume(): void
    {
        $user = User::factory()->create();

        $otherUser = User::factory()->create();

        $resume = Resume::create([
            'user_id' => $otherUser->id,
            'title' => 'Other User Resume',
            'file_name' => 'resume.pdf',
            'file_path' => 'resumes/test/other.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);

        $response = $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analyze"
            );

        $response->assertStatus(403);

        $this->assertDatabaseCount(
            'resume_analyses',
            0
        );
    }
}