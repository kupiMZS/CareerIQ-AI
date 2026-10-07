<?php

namespace App\Services;

use App\Models\Resume;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class CareerRecommendationService
{
    public function recommend(
        Resume $resume,
        ?string $careerGoal = null
    ): array {
        $resume->loadMissing([
            'user.profile',
            'analysis',
        ]);

        $profile = $resume->user->profile;
        $analysis = $resume->analysis;

        $payload = [
            'profile' => [
                'current_role' => $profile?->headline,
                'career_goal' => $careerGoal,
                'years_experience' => $profile?->years_experience,
                'education' => $analysis?->education ?? [],
                'interests' => [],
            ],
            'skills' => $analysis?->skills ?? [],
        ];

        $response = Http::timeout(30)
            ->post(
                config('services.ai_engine.url')
                    .'/career/recommend',
                $payload
            );

        if ($response->failed()) {
            throw new RuntimeException(
                'AI Engine returned HTTP '
                    .$response->status()
            );
        }

        $result = $response->json();

        if (! is_array($result)) {
            throw new RuntimeException(
                'AI Engine returned an invalid '
                    .'career recommendation response'
            );
        }

        return $result;
    }
}
