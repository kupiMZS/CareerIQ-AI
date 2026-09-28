<?php

namespace App\Services;

use App\Models\User;
use App\Models\UserProfile;

class ProfileService
{
    public function getProfile(User $user): ?UserProfile
    {
        return $user->profile;
    }

    public function createProfile(
        User $user,
        array $data
    ): UserProfile {

        return $user->profile()->create($data);

    }

    public function updateProfile(
        UserProfile $profile,
        array $data
    ): UserProfile {

        $profile->update($data);

        return $profile->fresh();

    }

    public function deleteProfile(
        UserProfile $profile
    ): bool {

        return $profile->delete();

    }
}
