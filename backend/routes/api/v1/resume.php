<?php

use App\Http\Controllers\Api\V1\ResumeController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {

    Route::post('/resumes', [ResumeController::class, 'store']);

    Route::get('/resumes', [ResumeController::class, 'index']);

    Route::delete('/resumes/{id}', [ResumeController::class, 'destroy']);

});
