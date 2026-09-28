<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('resumes', function (Blueprint $table) {

            $table->id();

            $table->foreignId('user_id')
                ->constrained()
                ->cascadeOnDelete();

            $table->string('title');

            $table->string('file_name');

            $table->string('file_path');

            $table->string('file_type')
                ->nullable();

            $table->unsignedBigInteger('file_size')
                ->nullable();

            $table->enum('status', [

                'uploaded',
                'processing',
                'completed',
                'failed',

            ])
                ->default('uploaded');

            $table->timestamps();

        });
    }

    public function down(): void
    {
        Schema::dropIfExists('resumes');
    }
};
