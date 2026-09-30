<?php

use App\Http\Controllers\Api\V1\ResumeAnalysisController;
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

});
