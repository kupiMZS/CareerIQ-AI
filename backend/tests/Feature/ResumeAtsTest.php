<?php

namespace Tests\Feature;

use App\Models\Resume;
use App\Models\User;
use App\Services\ResumeParserService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class ResumeAtsTest extends TestCase
{
    use RefreshDatabase;

    private function createResume(User $user): Resume
    {
        return Resume::create([
            'user_id' => $user->id,
            'title' => 'Synthetic ATS Resume',
            'file_name' => 'synthetic.pdf',
            'file_path' => 'resumes/test/synthetic.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);
    }

    private function fakeParser(
        Resume $resume,
        string $text
    ): void {
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

    private function validReport(): array
    {
        $codes = [
            'contact_email',
            'section_skills',
            'section_education',
            'section_experience',
            'section_skills_content',
            'section_education_content',
            'section_experience_content',
            'quantified_outcome_evidence',
        ];

        $findings = [];

        foreach ($codes as $code) {
            $findings[] = [
                'code' => $code,
                'status' => 'not_assessed',
                'explanation' => 'Synthetic test finding.',
                'supporting_text' => [],
                'recommendation' => null,
            ];
        }

        return [
            'report_version' => 'ats-v1',
            'score' => null,
            'findings' => $findings,
            'limitations' => [
                'Synthetic assessment only.',
            ],
        ];
    }

    private function atsUrl(Resume $resume): string
    {
        return "/api/v1/resumes/{$resume->id}/analysis/ats";
    }

    public function test_owner_can_request_ats_without_saving_analysis(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $text = "Skills\nPython\nExperience\nReduced errors by 20%.";

        $this->fakeParser($resume, $text);

        Http::fake([
            config('services.ai_engine.url').'/analyze/ats' => Http::response($this->validReport(), 200),
        ]);

        $response = $this->actingAs($user)
            ->postJson($this->atsUrl($resume));

        $response
            ->assertStatus(200)
            ->assertJsonPath('data.report_version', 'ats-v1')
            ->assertJsonPath('data.score', null)
            ->assertJsonCount(8, 'data.findings');

        $this->assertArrayNotHasKey(
            'ats_score',
            $response->json('data')
        );

        $this->assertDatabaseCount('resume_analyses', 0);

        Http::assertSent(
            fn ($request) => $request->url()
                    === config('services.ai_engine.url').'/analyze/ats'
                && $request->method() === 'POST'
                && $request['resume_text'] === $text
        );
    }

    public function test_guest_cannot_request_ats(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        Http::fake();

        $this->postJson($this->atsUrl($resume))
            ->assertStatus(401);

        Http::assertNothingSent();

        $this->assertDatabaseCount('resume_analyses', 0);
    }

    public function test_other_user_cannot_request_ats(): void
    {
        $owner = User::factory()->create();
        $other = User::factory()->create();
        $resume = $this->createResume($owner);

        Http::fake();

        $this->actingAs($other)
            ->postJson($this->atsUrl($resume))
            ->assertStatus(403);

        Http::assertNothingSent();

        $this->assertDatabaseCount('resume_analyses', 0);
    }

    public function test_upstream_failure_returns_safe_502(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $this->fakeParser(
            $resume,
            'Synthetic resume text'
        );

        Http::fake([
            config('services.ai_engine.url').'/analyze/ats' => Http::response(
                ['detail' => 'Synthetic upstream failure'],
                503
            ),
        ]);

        $this->actingAs($user)
            ->postJson($this->atsUrl($resume))
            ->assertStatus(502)
            ->assertJsonPath(
                'message',
                'Resume ATS service unavailable'
            );

        $this->assertDatabaseCount('resume_analyses', 0);
    }

    public function test_scored_upstream_report_is_rejected(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $this->fakeParser(
            $resume,
            'Synthetic resume text'
        );

        $invalid = $this->validReport();
        $invalid['score'] = 85;

        Http::fake([
            config('services.ai_engine.url').'/analyze/ats' => Http::response($invalid, 200),
        ]);

        $this->actingAs($user)
            ->postJson($this->atsUrl($resume))
            ->assertStatus(502)
            ->assertJsonPath(
                'message',
                'Resume ATS service unavailable'
            );

        $this->assertDatabaseCount('resume_analyses', 0);
    }

    public function test_duplicate_finding_code_is_rejected(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $this->fakeParser(
            $resume,
            'Synthetic resume text'
        );

        $invalid = $this->validReport();

        $invalid['findings'][1]['code'] = 'contact_email';

        Http::fake([
            config('services.ai_engine.url').'/analyze/ats' => Http::response($invalid, 200),
        ]);

        $this->actingAs($user)
            ->postJson($this->atsUrl($resume))
            ->assertStatus(502)
            ->assertJsonPath(
                'message',
                'Resume ATS service unavailable'
            );

        $this->assertDatabaseCount('resume_analyses', 0);
    }

    public function test_malformed_finding_is_rejected(): void
    {
        $user = User::factory()->create();
        $resume = $this->createResume($user);

        $this->fakeParser(
            $resume,
            'Synthetic resume text'
        );

        $invalid = $this->validReport();

        $invalid['findings'][0]['supporting_text']
            = 'Incorrect type';

        Http::fake([
            config('services.ai_engine.url').'/analyze/ats' => Http::response($invalid, 200),
        ]);

        $this->actingAs($user)
            ->postJson($this->atsUrl($resume))
            ->assertStatus(502)
            ->assertJsonPath(
                'message',
                'Resume ATS service unavailable'
            );

        $this->assertDatabaseCount('resume_analyses', 0);
    }
}
