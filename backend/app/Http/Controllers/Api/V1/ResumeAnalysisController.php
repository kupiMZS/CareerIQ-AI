<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Resources\ResumeAnalysisResource;
use App\Models\Resume;
use App\Services\ResumeAnalysisService;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Illuminate\Http\JsonResponse;

class ResumeAnalysisController extends Controller
{
    use AuthorizesRequests;

    public function __construct(
        private ResumeAnalysisService $analysisService
    ) {}

    public function analyze(
        Resume $resume
    ): JsonResponse {

        $this->authorize('view', $resume);

        $analysis = $this->analysisService
            ->createPendingAnalysis($resume);

        return response()->json([

            'message' => 'Resume analysis started',

            'data' => new ResumeAnalysisResource($analysis),

        ], 201);

    }

    public function show(
        Resume $resume
    ): ResumeAnalysisResource {

        $this->authorize('view', $resume);

        $analysis = $this->analysisService
            ->getAnalysis($resume);

        return new ResumeAnalysisResource($analysis);

    }
}
