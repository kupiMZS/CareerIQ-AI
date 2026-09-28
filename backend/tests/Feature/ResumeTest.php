<?php

namespace Tests\Feature;

use App\Models\Resume;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;
use Laravel\Sanctum\Sanctum;
use Tests\TestCase;

class ResumeTest extends TestCase
{
    use RefreshDatabase;

    public function test_authenticated_user_can_upload_resume(): void
    {

        Storage::fake('local');

        $user = User::factory()->create();

        Sanctum::actingAs($user);

        $file = UploadedFile::fake()
            ->create(
                'resume.pdf',
                100,
                'application/pdf'
            );

        $response = $this->postJson('/api/v1/resumes', [

            'title' => 'Software Engineer Resume',

            'file' => $file,

        ]);

        $response
            ->assertStatus(201)
            ->assertJson([
                'message' => 'Resume uploaded successfully',
            ]);

        $this->assertDatabaseHas('resumes', [

            'user_id' => $user->id,

            'title' => 'Software Engineer Resume',

        ]);

    }

    public function test_invalid_resume_file_fails(): void
    {

        $user = User::factory()->create();

        Sanctum::actingAs($user);

        $file = UploadedFile::fake()
            ->create(
                'resume.txt',
                100,
                'text/plain'
            );

        $response = $this->postJson('/api/v1/resumes', [

            'title' => 'Invalid Resume',

            'file' => $file,

        ]);

        $response
            ->assertStatus(422)
            ->assertJsonValidationErrors([
                'file',
            ]);

    }

    public function test_user_can_view_resumes(): void
    {

        $user = User::factory()->create();

        Resume::create([

            'user_id' => $user->id,

            'title' => 'My Resume',

            'file_name' => 'resume.pdf',

            'file_path' => 'resumes/1/resume.pdf',

            'file_type' => 'application/pdf',

            'file_size' => 1000,

            'status' => 'uploaded',

        ]);

        Sanctum::actingAs($user);

        $response = $this->getJson('/api/v1/resumes');

        $response
            ->assertStatus(200)
            ->assertJsonPath(
                'data.0.title',
                'My Resume'
            );

    }

    public function test_user_can_delete_resume(): void
    {

        $user = User::factory()->create();

        $resume = Resume::create([

            'user_id' => $user->id,

            'title' => 'Delete Resume',

            'file_name' => 'resume.pdf',

            'file_path' => 'resumes/1/resume.pdf',

            'file_type' => 'application/pdf',

            'file_size' => 1000,

            'status' => 'uploaded',

        ]);

        Sanctum::actingAs($user);

        $response = $this->deleteJson(
            "/api/v1/resumes/{$resume->id}"
        );

        $response
            ->assertStatus(200);

        $this->assertDatabaseMissing(
            'resumes',
            [
                'id' => $resume->id,
            ]
        );

    }
}
