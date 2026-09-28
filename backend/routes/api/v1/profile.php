<?php

use App\Http\Controllers\Api\V1\ProfileController;
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {

    Route::get('/profile', [ProfileController::class, 'show']);

    Route::post('/profile', [ProfileController::class, 'store']);

    Route::put('/profile', [ProfileController::class, 'update']);

    Route::delete('/profile', [ProfileController::class, 'destroy']);

});
