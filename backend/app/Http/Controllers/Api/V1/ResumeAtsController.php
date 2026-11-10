<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Models\Resume;
use App\Services\ResumeAtsService;
use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Illuminate\Http\JsonResponse;
use Throwable;

class ResumeAtsController extends Controller
{
    use AuthorizesRequests;

    public function __construct(
        private ResumeAtsService $atsService
    ) {}

    public function show(Resume $resume): JsonResponse
    {
        $this->authorize('view', $resume);

        try {
            $report = $this->atsService->generate($resume);
        } catch (Throwable $exception) {
            report($exception);

            return response()->json([
                'message' => 'Resume ATS service unavailable',
            ], 502);
        }

        return response()->json([
            'message' => 'Resume ATS report generated successfully',
            'data' => $report,
        ]);
    }
}
