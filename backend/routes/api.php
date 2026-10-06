<?php

use Illuminate\Support\Facades\Route;

Route::prefix('v1')->group(function () {
    require base_path('routes/api/v1/auth.php');

    require base_path('routes/api/v1/profile.php');

    require base_path('routes/api/v1/resume.php');

    require base_path(
        'routes/api/v1/resume_analysis.php'
    );

    require base_path(
        'routes/api/v1/career_recommendation.php'
    );
});
