<?php

namespace App\Http\Controllers\Api\V1;


use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\LoginRequest;
use App\Http\Requests\Auth\RegisterRequest;
use App\Http\Resources\UserResource;
use App\Services\AuthService;
use Illuminate\Http\Request;
use App\Http\Responses\ApiResponse;


class AuthController extends Controller
{

    public function __construct(
        private AuthService $authService
    ) {
    }


    public function register(RegisterRequest $request)
    {

        $user = $this->authService->register(
            $request->validated()
        );


        $token = $user
            ->createToken('auth-token')
            ->plainTextToken;


        return ApiResponse::success(

            'Registration successful',

            [

                'user' => new UserResource($user),

                'token' => $token

            ],

            201

        );

    }



    public function login(LoginRequest $request)
    {

        $user = $this->authService->login(
            $request->validated()
        );


        if (!$user) {

            return ApiResponse::error(
                'Invalid credentials',
                401
            );

        }


        $token = $user
            ->createToken('auth-token')
            ->plainTextToken;


        return ApiResponse::success(

            'Login successful',

            [

                'user' => new UserResource($user),

                'token' => $token

            ]

        );

    }



    public function logout(Request $request)
    {

        $request
            ->user()
            ->currentAccessToken()
            ->delete();


        return ApiResponse::success(
            'Logged out successfully'
        );

    }



    public function user(Request $request)
    {

        return ApiResponse::success(

            'User retrieved successfully',

            new UserResource(
                $request->user()
            )

        );

    }

}
