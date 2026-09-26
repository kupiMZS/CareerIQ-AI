<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;


class AuthTest extends TestCase
{

    use RefreshDatabase;



    public function test_user_can_register(): void
    {

        $response = $this->postJson('/api/v1/register', [

            'name' => 'Test User',

            'email' => 'test@example.com',

            'password' => 'password123',

        ]);


        $response
            ->assertStatus(201)
            ->assertJson([
                'success' => true,
                'message' => 'Registration successful'
            ]);


        $this->assertDatabaseHas('users', [

            'email' => 'test@example.com'

        ]);

    }




    public function test_duplicate_email_registration_fails(): void
    {

        User::factory()->create([

            'email' => 'test@example.com'

        ]);


        $response = $this->postJson('/api/v1/register', [

            'name' => 'Another User',

            'email' => 'test@example.com',

            'password' => 'password123',

        ]);


        $response
            ->assertStatus(422);

    }




    public function test_user_can_login(): void
    {

        User::factory()->create([

            'email' => 'test@example.com',

            'password' => bcrypt('password123')

        ]);


        $response = $this->postJson('/api/v1/login', [

            'email' => 'test@example.com',

            'password' => 'password123',

        ]);


        $response
            ->assertStatus(200)
            ->assertJson([
                'success' => true,
                'message' => 'Login successful'
            ]);


        $this->assertNotEmpty(
            $response->json('data.token')
        );

    }




    public function test_invalid_password_fails(): void
    {

        User::factory()->create([

            'email' => 'test@example.com',

            'password' => bcrypt('password123')

        ]);


        $response = $this->postJson('/api/v1/login', [

            'email' => 'test@example.com',

            'password' => 'wrong-password',

        ]);


        $response
            ->assertStatus(401);

    }




    public function test_authenticated_user_can_access_profile(): void
    {

        $user = User::factory()->create();


        $token = $user
            ->createToken('test-token')
            ->plainTextToken;


        $response = $this
            ->withHeader(
                'Authorization',
                'Bearer '.$token
            )
            ->getJson('/api/v1/user');


        $response
            ->assertStatus(200)
            ->assertJson([
                'success' => true
            ]);

    }




    public function test_user_can_logout(): void
    {

        $user = User::factory()->create();


        $token = $user
            ->createToken('test-token')
            ->plainTextToken;


        $response = $this
            ->withHeader(
                'Authorization',
                'Bearer '.$token
            )
            ->postJson('/api/v1/logout');


        $response
            ->assertStatus(200)
            ->assertJson([
                'success' => true,
                'message' => 'Logged out successfully'
            ]);

    }

}
