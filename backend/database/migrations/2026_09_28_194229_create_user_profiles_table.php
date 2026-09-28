<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('user_profiles', function (Blueprint $table) {

            $table->id();

            $table->foreignId('user_id')
                ->constrained()
                ->cascadeOnDelete();

            $table->string('first_name')
                ->nullable();

            $table->string('last_name')
                ->nullable();

            $table->string('phone')
                ->nullable();

            $table->string('location')
                ->nullable();

            $table->string('country')
                ->nullable();

            $table->string('headline')
                ->nullable();

            $table->text('summary')
                ->nullable();

            $table->string('linkedin_url')
                ->nullable();

            $table->string('github_url')
                ->nullable();

            $table->string('portfolio_url')
                ->nullable();

            $table->integer('years_experience')
                ->default(0);

            $table->timestamps();

        });
    }

    public function down(): void
    {
        Schema::dropIfExists('user_profiles');
    }
};
