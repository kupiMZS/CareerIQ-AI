<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\Profile\StoreProfileRequest;
use App\Http\Requests\Profile\UpdateProfileRequest;
use App\Http\Resources\UserProfileResource;
use App\Http\Responses\ApiResponse;
use App\Services\ProfileService;
use Illuminate\Database\UniqueConstraintViolationException;
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
            $profile === null ? null : new UserProfileResource($profile)
        );

    }

    public function store(
        StoreProfileRequest $request
    ) {

        if ($request->user()->profile()->exists()) {
            return ApiResponse::error(
                'Profile already exists',
                409
            );
        }

        try {
            $profile = $this->profileService
                ->createProfile(
                    $request->user(),
                    $request->validated()
                );
        } catch (UniqueConstraintViolationException $exception) {
            if ($request->user()->profile()->exists()) {
                return ApiResponse::error(
                    'Profile already exists',
                    409
                );
            }

            throw $exception;
        }

        return ApiResponse::success(
            'Profile created successfully',
            new UserProfileResource($profile),
            201
        );

    }

    public function update(
        UpdateProfileRequest $request
    ) {

        $existingProfile = $request->user()->profile;

        if ($existingProfile === null) {
            return ApiResponse::error('Profile not found', 404);
        }

        $profile = $this->profileService
            ->updateProfile(
                $existingProfile,
                $request->validated()
            );

        return ApiResponse::success(
            'Profile updated successfully',
            new UserProfileResource($profile)
        );

    }

    public function destroy(Request $request)
    {

        $profile = $request->user()->profile;

        if ($profile === null) {
            return ApiResponse::error('Profile not found', 404);
        }

        $this->profileService
            ->deleteProfile(
                $profile
            );

        return ApiResponse::success(
            'Profile deleted successfully'
        );

    }
}
