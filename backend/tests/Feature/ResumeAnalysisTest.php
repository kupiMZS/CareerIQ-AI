<?php

namespace Tests\Feature;

use App\Models\Resume;
use App\Models\ResumeAnalysis;
use App\Models\User;
use App\Services\ResumeParserService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ResumeAnalysisTest extends TestCase
{
    use RefreshDatabase;

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

        $this->mock(ResumeParserService::class, function ($mock) {
            $mock->shouldReceive('extractText')
                ->once()
                ->withArgs(fn ($resume) => $resume instanceof Resume)
                ->andReturn('John Doe Software Engineer Laravel Angular');
        });

        $response = $this->actingAs($user)
            ->postJson("/api/v1/resumes/{$resume->id}/analyze");

        $response
            ->assertStatus(201)
            ->assertJsonPath('data.resume_id', $resume->id)
            ->assertJsonPath('data.ats_score', 50)
            ->assertJsonPath('data.status', 'completed');

        $this->assertDatabaseHas('resume_analyses', [
            'resume_id' => $resume->id,
            'ats_score' => 50,
            'status' => 'completed',
            'summary' => 'John Doe Software Engineer Laravel Angular',
        ]);
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

        $this->mock(ResumeParserService::class, function ($mock) {
            $mock->shouldReceive('extractText')
                ->twice()
                ->andReturn('Test resume content');
        });

        $this->actingAs($user)
            ->postJson("/api/v1/resumes/{$resume->id}/analyze")
            ->assertStatus(201);

        $this->actingAs($user)
            ->postJson("/api/v1/resumes/{$resume->id}/analyze")
            ->assertStatus(201);

        $this->assertDatabaseCount('resume_analyses', 1);

        $this->assertDatabaseHas('resume_analyses', [
            'resume_id' => $resume->id,
            'status' => 'completed',
        ]);
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
            'skills' => ['Laravel', 'Angular'],
            'summary' => 'Strong software engineering resume.',
            'status' => 'completed',
        ]);

        $response = $this->actingAs($user)
            ->getJson("/api/v1/resumes/{$resume->id}/analysis");

        $response
            ->assertStatus(200)
            ->assertJsonPath('data.resume_id', $resume->id)
            ->assertJsonPath('data.ats_score', 85)
            ->assertJsonPath('data.status', 'completed');
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
            ->postJson("/api/v1/resumes/{$resume->id}/analyze");

        $response->assertStatus(403);

        $this->assertDatabaseCount('resume_analyses', 0);
    }
}
