<?php

namespace Tests\Feature;

use App\Models\User;
use App\Models\UserProfile;
use App\Services\ProfileService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class ProfileEdgeCasesTest extends TestCase
{
    use RefreshDatabase;

    public function test_guests_cannot_access_profile_routes(): void
    {
        $this->getJson('/api/v1/profile')
            ->assertUnauthorized();

        $this->postJson('/api/v1/profile', [
            'first_name' => 'Guest',
        ])->assertUnauthorized();

        $this->putJson('/api/v1/profile', [
            'first_name' => 'Guest',
        ])->assertUnauthorized();

        $this->deleteJson('/api/v1/profile')
            ->assertUnauthorized();
    }

    public function test_missing_profile_is_returned_as_null(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user);

        $this->getJson('/api/v1/profile')
            ->assertOk()
            ->assertJsonPath('success', true)
            ->assertJsonPath('data', null);
    }

    public function test_updating_missing_profile_returns_404(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user);

        $this->putJson('/api/v1/profile', [
            'headline' => 'Software Engineer',
        ])->assertNotFound();

        $this->assertDatabaseCount('user_profiles', 0);
    }

    public function test_deleting_missing_profile_returns_404(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user);

        $this->deleteJson('/api/v1/profile')
            ->assertNotFound();

        $this->assertDatabaseCount('user_profiles', 0);
    }

    public function test_duplicate_profile_creation_returns_409(): void
    {
        $user = User::factory()->create();

        UserProfile::create([
            'user_id' => $user->id,
            'first_name' => 'Existing',
        ]);

        Sanctum::actingAs($user);

        $this->postJson('/api/v1/profile', [
            'first_name' => 'Duplicate',
        ])->assertStatus(409);

        $this->assertDatabaseCount('user_profiles', 1);

        $this->assertDatabaseHas('user_profiles', [
            'user_id' => $user->id,
            'first_name' => 'Existing',
        ]);
    }

    public function test_concurrent_profile_creation_returns_409(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user);

        // Simulate another request inserting the profile after
        // the controller's initial existence check.
        $this->app->instance(
            ProfileService::class,
            new class extends ProfileService
            {
                public function createProfile(
                    User $user,
                    array $data
                ): UserProfile {
                    $user->profile()->create([
                        'first_name' => 'First request',
                    ]);

                    return parent::createProfile($user, $data);
                }
            }
        );

        $this->postJson('/api/v1/profile', [
            'first_name' => 'Second request',
        ])->assertStatus(409)
            ->assertJsonPath('success', false)
            ->assertJsonPath('message', 'Profile already exists');

        $this->assertDatabaseCount('user_profiles', 1);

        $this->assertDatabaseHas('user_profiles', [
            'user_id' => $user->id,
            'first_name' => 'First request',
        ]);
    }

    public function test_creating_profile_rejects_null_experience(): void
    {
        $user = User::factory()->create();

        Sanctum::actingAs($user);

        $this->postJson('/api/v1/profile', [
            'first_name' => 'Example',
            'years_experience' => null,
        ])->assertUnprocessable()
            ->assertJsonValidationErrors('years_experience');

        $this->assertDatabaseCount('user_profiles', 0);
    }

    public function test_updating_profile_rejects_null_experience(): void
    {
        $user = User::factory()->create();

        UserProfile::create([
            'user_id' => $user->id,
            'years_experience' => 3,
        ]);

        Sanctum::actingAs($user);

        $this->putJson('/api/v1/profile', [
            'years_experience' => null,
        ])->assertUnprocessable()
            ->assertJsonValidationErrors('years_experience');

        $this->assertDatabaseHas('user_profiles', [
            'user_id' => $user->id,
            'years_experience' => 3,
        ]);
    }

    public function test_user_updates_only_their_own_profile(): void
    {
        $alice = User::factory()->create();
        $bob = User::factory()->create();

        UserProfile::create([
            'user_id' => $alice->id,
            'first_name' => 'Alice',
        ]);

        UserProfile::create([
            'user_id' => $bob->id,
            'first_name' => 'Bob',
        ]);

        Sanctum::actingAs($alice);

        $this->putJson('/api/v1/profile', [
            'first_name' => 'Updated Alice',
        ])->assertOk();

        $this->assertDatabaseHas('user_profiles', [
            'user_id' => $alice->id,
            'first_name' => 'Updated Alice',
        ]);

        $this->assertDatabaseHas('user_profiles', [
            'user_id' => $bob->id,
            'first_name' => 'Bob',
        ]);
    }
}
