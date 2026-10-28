<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Models\Resume;
use App\Services\ResumeEvidenceService;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Illuminate\Http\JsonResponse;
use Throwable;

class ResumeEvidenceController extends Controller
{
    use AuthorizesRequests;

    public function __construct(
        private ResumeEvidenceService $evidenceService
    ) {}

    public function show(Resume $resume): JsonResponse
    {
        $this->authorize('view', $resume);

        try {
            $report = $this->evidenceService
                ->generate($resume);
        } catch (Throwable $exception) {
            report($exception);

            return response()->json([
                'message' => 'Resume evidence service unavailable',
            ], 502);
        }

        return response()->json([
            'message' => 'Resume evidence generated successfully',
            'data' => $report,
        ]);
    }
}
