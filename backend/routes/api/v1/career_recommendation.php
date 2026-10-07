<?php

use App\Http\Controllers\Api\V1\CareerRecommendationController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {
    Route::post(
        '/resumes/{resume}/career/recommend',
        [
            CareerRecommendationController::class,
            'recommend',
        ]
    );
});
