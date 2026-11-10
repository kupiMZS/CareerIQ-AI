<?php

use App\Http\Controllers\Api\V1\ResumeAnalysisController;
use App\Http\Controllers\Api\V1\ResumeAtsController;
use App\Http\Controllers\Api\V1\ResumeEvidenceController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {

    Route::post(
        '/resumes/{resume}/analyze',
        [ResumeAnalysisController::class, 'analyze']
    );

    Route::get(
        '/resumes/{resume}/analysis',
        [ResumeAnalysisController::class, 'show']
    );

    Route::post(
        '/resumes/{resume}/analysis/evidence',
        [ResumeEvidenceController::class, 'show']
    );

    Route::post(
        '/resumes/{resume}/analysis/ats',
        [ResumeAtsController::class, 'show']
    );

});
