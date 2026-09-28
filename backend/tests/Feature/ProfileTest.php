<?php

namespace Tests\Feature;

use App\Models\User;
use App\Models\UserProfile;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class ProfileTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_create_profile(): void
    {

        $user = User::factory()->create();

        Sanctum::actingAs($user);

        $response = $this->postJson('/api/v1/profile', [

            'first_name' => 'Kausar',

            'last_name' => 'Hossein',

            'headline' => 'Software Engineer',

            'years_experience' => 3,

        ]);

        $response
            ->assertStatus(201)
            ->assertJson([
                'message' => 'Profile created successfully',
            ]);

        $this->assertDatabaseHas('user_profiles', [

            'user_id' => $user->id,

            'first_name' => 'Kausar',

        ]);

    }

    public function test_user_can_view_profile(): void
    {

        $user = User::factory()->create();

        UserProfile::create([

            'user_id' => $user->id,

            'first_name' => 'Kausar',

            'years_experience' => 3,

        ]);

        Sanctum::actingAs($user);

        $response = $this->getJson('/api/v1/profile');

        $response
            ->assertStatus(200)
            ->assertJsonPath(
                'data.first_name',
                'Kausar'
            );

    }

    public function test_user_can_update_profile(): void
    {

        $user = User::factory()->create();

        $profile = UserProfile::create([

            'user_id' => $user->id,

            'first_name' => 'Old',

        ]);

        Sanctum::actingAs($user);

        $response = $this->putJson('/api/v1/profile', [

            'first_name' => 'New',

        ]);

        $response
            ->assertStatus(200);

        $this->assertDatabaseHas(
            'user_profiles',
            [
                'id' => $profile->id,
                'first_name' => 'New',
            ]
        );

    }

    public function test_user_can_delete_profile(): void
    {

        $user = User::factory()->create();

        UserProfile::create([

            'user_id' => $user->id,

            'first_name' => 'Kausar',

        ]);

        Sanctum::actingAs($user);

        $response = $this->deleteJson('/api/v1/profile');

        $response
            ->assertStatus(200);

        $this->assertDatabaseCount(
            'user_profiles',
            0
        );

    }
}
