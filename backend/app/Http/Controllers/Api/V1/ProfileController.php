<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\Profile\StoreProfileRequest;
use App\Http\Requests\Profile\UpdateProfileRequest;
use App\Http\Resources\UserProfileResource;
use App\Http\Responses\ApiResponse;
use App\Services\ProfileService;
use Illuminate\Http\Request;

class ProfileController extends Controller
{
    public function __construct(
        private ProfileService $profileService
    ) {}

    public function show(Request $request)
    {

        $profile = $this->profileService
            ->getProfile($request->user());

        return ApiResponse::success(
            'Profile retrieved successfully',
            new UserProfileResource($profile)
        );

    }

    public function store(
        StoreProfileRequest $request
    ) {

        $profile = $this->profileService
            ->createProfile(
                $request->user(),
                $request->validated()
            );

        return ApiResponse::success(
            'Profile created successfully',
            new UserProfileResource($profile),
            201
        );

    }

    public function update(
        UpdateProfileRequest $request
    ) {

        $profile = $this->profileService
            ->updateProfile(
                $request->user()->profile,
                $request->validated()
            );

        return ApiResponse::success(
            'Profile updated successfully',
            new UserProfileResource($profile)
        );

    }

    public function destroy(Request $request)
    {

        $this->profileService
            ->deleteProfile(
                $request->user()->profile
            );

        return ApiResponse::success(
            'Profile deleted successfully'
        );

    }
}
