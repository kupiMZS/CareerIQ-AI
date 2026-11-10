<?php

namespace Tests\Feature;

use App\Models\Resume;
use App\Models\User;
use App\Services\ResumeParserService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class ResumeEvidenceTest extends TestCase
{
    use RefreshDatabase;

    private function createResume(User $user): Resume
    {
        return Resume::create([
            'user_id' => $user->id,
            'title' => 'Synthetic Test Resume',
            'file_name' => 'synthetic.pdf',
            'file_path' => 'resumes/test/synthetic.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);
    }

    private function fakeParser(Resume $resume, string $text): void
    {
        $this->mock(
            ResumeParserService::class,
            function ($mock) use ($resume, $text) {
                $mock->shouldReceive('extractText')
                    ->once()
                    ->withArgs(
                        fn ($candidate) => $candidate instanceof Resume
                            && $candidate->id === $resume->id
                    )
                    ->andReturn($text);
            }
        );
    }

    public function test_owner_can_request_evidence_without_saving_analysis(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $text = "Skills\nPython\nNever used Docker\nPlan to learn AWS";

        $this->fakeParser($resume, $text);

        $report = [
            'analysis' => [
                'ats_score' => 50,
                'extracted_name' => 'Synthetic Person',
                'extracted_email' => 'synthetic@example.com',
                'skills' => ['Python', 'Docker', 'AWS'],
                'education' => [],
                'experience' => [],
                'summary' => 'Synthetic analysis summary.',
                'status' => 'completed',
            ],
            'skill_evidence' => [
                [
                    'field_path' => 'skills[0].name',
                    'skill_name' => 'Python',
                    'status' => 'literal_mention_only',
                    'review_flags' => [],
                ],
                [
                    'field_path' => 'skills[1].name',
                    'skill_name' => 'Docker',
                    'status' => 'explicit_rejection_only',
                    'review_flags' => [],
                ],
                [
                    'field_path' => 'skills[2].name',
                    'skill_name' => 'AWS',
                    'status' => 'literal_mention_only',
                    'review_flags' => [
                        'aspirational_wording',
                    ],
                ],
            ],
        ];

        Http::fake([
            config('services.ai_engine.url')
                .'/analyze/evidence' => Http::response(
                    $report,
                    200
                ),
        ]);

        $response = $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analysis/evidence"
            );

        $response
            ->assertStatus(200)
            ->assertJsonPath(
                'data.analysis.ats_score',
                50
            )
            ->assertJsonPath(
                'data.skill_evidence.0.skill_name',
                'Python'
            )
            ->assertJsonPath(
                'data.skill_evidence.1.status',
                'explicit_rejection_only'
            )
            ->assertJsonPath(
                'data.skill_evidence.2.review_flags.0',
                'aspirational_wording'
            );

        $this->assertDatabaseCount(
            'resume_analyses',
            0
        );

        Http::assertSent(
            fn ($request) => $request->url()
                    === config('services.ai_engine.url')
                        .'/analyze/evidence'
                && $request->method() === 'POST'
                && $request['resume_text'] === $text
        );
    }

    public function test_guest_cannot_request_evidence(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        Http::fake();

        $this->postJson(
            "/api/v1/resumes/{$resume->id}/analysis/evidence"
        )->assertStatus(401);

        Http::assertNothingSent();

        $this->assertDatabaseCount(
            'resume_analyses',
            0
        );
    }

    public function test_user_cannot_request_another_users_evidence(): void
    {
        $owner = User::factory()->create();
        $otherUser = User::factory()->create();

        $resume = $this->createResume($owner);

        Http::fake();

        $this->actingAs($otherUser)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analysis/evidence"
            )
            ->assertStatus(403);

        Http::assertNothingSent();

        $this->assertDatabaseCount(
            'resume_analyses',
            0
        );
    }

    public function test_ai_engine_failure_returns_bad_gateway(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $this->fakeParser(
            $resume,
            'Synthetic resume text'
        );

        Http::fake([
            config('services.ai_engine.url')
                .'/analyze/evidence' => Http::response(
                    ['detail' => 'Service unavailable'],
                    503
                ),
        ]);

        $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analysis/evidence"
            )
            ->assertStatus(502)
            ->assertJsonPath(
                'message',
                'Resume evidence service unavailable'
            );

        $this->assertDatabaseCount(
            'resume_analyses',
            0
        );
    }

    public function test_invalid_ai_response_returns_bad_gateway(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $this->fakeParser(
            $resume,
            'Synthetic resume text'
        );

        Http::fake([
            config('services.ai_engine.url')
                .'/analyze/evidence' => Http::response(
                    [
                        'analysis' => 'invalid',
                        'skill_evidence' => [],
                    ],
                    200
                ),
        ]);

        $this->actingAs($user)
            ->postJson(
                "/api/v1/resumes/{$resume->id}/analysis/evidence"
            )
            ->assertStatus(502)
            ->assertJsonPath(
                'message',
                'Resume evidence service unavailable'
            );

        $this->assertDatabaseCount(
            'resume_analyses',
            0
        );
    }
}
