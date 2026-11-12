<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Stop safely if historical duplicate profiles exist.
        // Do not delete or silently merge any user data.
        $hasDuplicates = DB::table('user_profiles')
            ->select('user_id')
            ->groupBy('user_id')
            ->havingRaw('COUNT(*) > 1')
            ->exists();

        if ($hasDuplicates) {
            throw new RuntimeException(
                'Cannot add unique constraint: duplicate user_profiles.user_id values exist.'
            );
        }

        Schema::table('user_profiles', function (Blueprint $table): void {
            $table->unique('user_id', 'user_profiles_user_id_unique');
        });
    }

    public function down(): void
    {
        // MySQL must retain an index supporting the user_id foreign key.
        // Adding the unique index may replace the original FK index.
        if (DB::connection()->getDriverName() === 'mysql') {
            $hasSupportingIndex = false;

            foreach (Schema::getIndexes('user_profiles') as $index) {
                if (
                    $index['name'] !== 'user_profiles_user_id_unique'
                    && ($index['columns'][0] ?? null) === 'user_id'
                ) {
                    $hasSupportingIndex = true;
                    break;
                }
            }

            if (! $hasSupportingIndex) {
                Schema::table(
                    'user_profiles',
                    function (Blueprint $table): void {
                        $table->index(
                            'user_id',
                            'user_profiles_user_id_fk_support'
                        );
                    }
                );
            }
        }

        Schema::table('user_profiles', function (Blueprint $table): void {
            $table->dropUnique('user_profiles_user_id_unique');
        });
    }
};
