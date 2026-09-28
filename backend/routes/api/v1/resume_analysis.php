<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\V1\ResumeAnalysisController;


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
