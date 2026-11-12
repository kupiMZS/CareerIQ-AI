<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Database\QueryException;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Tests\TestCase;

class ProfileUniquenessConstraintTest extends TestCase
{
    use RefreshDatabase;

    public function test_database_rejects_duplicate_profiles_for_same_user(): void
    {
        $user = User::factory()->create();

        DB::table('user_profiles')->insert([
            'user_id' => $user->id,
            'years_experience' => 2,
        ]);

        $this->expectException(QueryException::class);

        DB::table('user_profiles')->insert([
            'user_id' => $user->id,
            'years_experience' => 5,
        ]);
    }

    public function test_different_users_can_each_have_a_profile(): void
    {
        $firstUser = User::factory()->create();
        $secondUser = User::factory()->create();

        DB::table('user_profiles')->insert([
            [
                'user_id' => $firstUser->id,
                'years_experience' => 2,
            ],
            [
                'user_id' => $secondUser->id,
                'years_experience' => 5,
            ],
        ]);

        $this->assertSame(
            2,
            DB::table('user_profiles')->count()
        );
    }

    public function test_migration_refuses_existing_duplicates_without_deleting_them(): void
    {
        $user = User::factory()->create();

        // Simulate the old schema using the actual migration rollback.
        // This preserves the supporting FK index on MySQL.
        $migration = require database_path(
            'migrations/2026_11_10_000001_add_unique_constraint_to_user_profiles_user_id.php'
        );
        $migration->down();

        DB::table('user_profiles')->insert([
            [
                'user_id' => $user->id,
                'years_experience' => 2,
            ],
            [
                'user_id' => $user->id,
                'years_experience' => 5,
            ],
        ]);

        try {
            $migration->up();

            $this->fail(
                'The migration should reject existing duplicate profiles.'
            );
        } catch (\RuntimeException $exception) {
            $this->assertStringContainsString(
                'duplicate user_profiles.user_id',
                $exception->getMessage()
            );
        }

        // Confirm that the failed migration did not delete either row.
        $this->assertSame(
            2,
            DB::table('user_profiles')
                ->where('user_id', $user->id)
                ->count()
        );
    }
}
