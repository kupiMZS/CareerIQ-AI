<?php

namespace Tests\Feature;

use App\Models\Resume;
use App\Models\ResumeAnalysis;
use App\Models\User;
use App\Models\UserProfile;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class CareerRecommendationTest extends TestCase
{
    use RefreshDatabase;

    private function createResume(
        User $user
    ): Resume {
        return Resume::create([
            'user_id' => $user->id,
            'title' => 'Career Resume',
            'file_name' => 'career-resume.pdf',
            'file_path' => 'resumes/test/career-resume.pdf',
            'file_type' => 'application/pdf',
            'file_size' => 1000,
            'status' => 'uploaded',
        ]);
    }

    private function fakeCareerEngine(
        array $overrides = []
    ): void {
        $response = array_replace([
            'recommendation_version' => '1.0',
            'status' => 'ok',
            'recommendations' => [
                [
                    'career_title' => 'Data Engineer',
                    'match_score' => 0.8,
                    'rationale' => 'Strong Python and database skills.',
                    'matched_skills' => [
                        'Python',
                        'PostgreSQL',
                    ],
                    'missing_skills' => [
                        'Apache Airflow',
                    ],
                    'entry_level' => false,
                ],
            ],
            'roadmap' => [
                [
                    'step' => 1,
                    'title' => 'Build Apache Airflow proficiency',
                    'description' => 'Build a data pipeline project.',
                    'skills' => [
                        'Apache Airflow',
                    ],
                ],
            ],
            'missing_information' => [],
        ], $overrides);

        Http::fake([
            config('services.ai_engine.url')
                .'/career/recommend' => Http::response(
                    $response,
                    200
                ),
        ]);
    }

    public function test_authenticated_user_can_generate_career_recommendation(): void
    {
        $user = User::factory()->create();

        UserProfile::create([
            'user_id' => $user->id,
            'headline' => 'Backend Engineer',
            'years_experience' => 3,
        ]);

        $resume = $this->createResume($user);

        ResumeAnalysis::create([
            'resume_id' => $resume->id,
            'skills' => [
                'Python',
                'PostgreSQL',
            ],
            'education' => [
                'BSc Computer Science',
            ],
            'status' => 'completed',
        ]);

        Sanctum::actingAs($user);

        $this->fakeCareerEngine();

        $response = $this->postJson(
            "/api/v1/resumes/{$resume->id}/career/recommend",
            [
                'career_goal' => 'Data Engineer',
            ]
        );

        $response
            ->assertStatus(200)
            ->assertJsonPath(
                'message',
                'Career recommendations generated successfully'
            )
            ->assertJsonPath(
                'data.status',
                'ok'
            )
            ->assertJsonPath(
                'data.recommendation_version',
                '1.0'
            )
            ->assertJsonPath(
                'data.recommendations.0.career_title',
                'Data Engineer'
            );

        Http::assertSent(
            function ($request) {
                return $request->url()
                    === config(
                        'services.ai_engine.url'
                    ).'/career/recommend'
                    && $request->method() === 'POST'
                    && $request[
                        'profile'
                    ][
                        'current_role'
                    ] === 'Backend Engineer'
                    && $request[
                        'profile'
                    ][
                        'career_goal'
                    ] === 'Data Engineer'
                    && $request[
                        'profile'
                    ][
                        'years_experience'
                    ] === 3
                    && $request[
                        'profile'
                    ][
                        'education'
                    ] === [
                        'BSc Computer Science',
                    ]
                    && $request['skills'] === [
                        'Python',
                        'PostgreSQL',
                    ];
            }
        );
    }

    public function test_career_recommendation_supports_missing_profile_and_analysis(): void
    {
        $user = User::factory()->create();

        $resume = $this->createResume($user);

        Sanctum::actingAs($user);

        $this->fakeCareerEngine([
            'status' => 'needs_more_information',
            'recommendations' => [],
            'roadmap' => [],
            'missing_information' => [
                'skills',
                'career_goal',
            ],
        ]);

        $response = $this->postJson(
            "/api/v1/resumes/{$resume->id}/career/recommend"
        );

        $response
            ->assertStatus(200)
            ->assertJsonPath(
                'data.status',
                'needs_more_information'
            )
            ->assertJsonPath(
                'data.recommendations',
                []
            )
            ->assertJsonPath(
                'data.roadmap',
                []
            );

        Http::assertSent(
            function ($request) {
                return $request[
                    'profile'
                ][
                    'current_role'
                ] === null
                    && $request[
                        'profile'
                    ][
                        'career_goal'
                    ] === null
                    && $request[
                        'profile'
                    ][
                        'years_experience'
                    ] === null
                    && $request[
                        'profile'
                    ][
                        'education'
                    ] === []
                    && $request[
                        'profile'
                    ][
                        'interests'
                    ] === []
                    && $request[
                        'skills'
                    ] === [];
            }
        );
    }

    public function test_ai_engine_failure_returns_bad_gateway(): void
    {
        $user = User::factory()->create();

        $resume = $this->createResume($user);

        Sanctum::actingAs($user);

        Http::fake([
            config('services.ai_engine.url')
                .'/career/recommend' => Http::failedConnection(),
        ]);

        $response = $this->postJson(
            "/api/v1/resumes/{$resume->id}/career/recommend",
            [
                'career_goal' => 'Backend Engineer',
            ]
        );

        $response
            ->assertStatus(502)
            ->assertJson([
                'message' => 'Career recommendation service unavailable',
            ]);
    }

    public function test_user_cannot_generate_recommendation_for_another_users_resume(): void
    {
        $user = User::factory()->create();

        $otherUser = User::factory()->create();

        $resume = $this->createResume(
            $otherUser
        );

        Sanctum::actingAs($user);

        Http::fake();

        $response = $this->postJson(
            "/api/v1/resumes/{$resume->id}/career/recommend"
        );

        $response->assertStatus(403);

        Http::assertNothingSent();
    }

    public function test_career_goal_validation(): void
    {
        $user = User::factory()->create();

        $resume = $this->createResume($user);

        Sanctum::actingAs($user);

        $response = $this->postJson(
            "/api/v1/resumes/{$resume->id}/career/recommend",
            [
                'career_goal' => [
                    'invalid',
                ],
            ]
        );

        $response->assertStatus(422);
    }
}
