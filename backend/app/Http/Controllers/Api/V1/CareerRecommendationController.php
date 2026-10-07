<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\Career\GenerateCareerRecommendationRequest;
use App\Models\Resume;
use App\Services\CareerRecommendationService;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Illuminate\Http\JsonResponse;
use Throwable;

class CareerRecommendationController extends Controller
{
    use AuthorizesRequests;

    public function __construct(
        private CareerRecommendationService $recommendationService
    ) {}

    public function recommend(
        GenerateCareerRecommendationRequest $request,
        Resume $resume
    ): JsonResponse {
        $this->authorize('view', $resume);

        $validated = $request->validated();

        try {
            $recommendation = $this->recommendationService
                ->recommend(
                    $resume,
                    $validated['career_goal'] ?? null
                );
        } catch (Throwable $exception) {
            report($exception);

            return response()->json([
                'message' => 'Career recommendation service unavailable',
            ], 502);
        }

        return response()->json([
            'message' => 'Career recommendations generated successfully',
            'data' => $recommendation,
        ]);
    }
}
