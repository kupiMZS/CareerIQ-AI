<?php

namespace App\Http\Responses;

class ApiResponse
{
    public static function success(
        string $message,
        mixed $data = null,
        int $status = 200
    ) {

        return response()->json([

            'success' => true,

            'message' => $message,

            'data' => $data,

        ], $status);

    }

    public static function error(
        string $message,
        int $status = 400,
        mixed $errors = null
    ) {

        return response()->json([

            'success' => false,

            'message' => $message,

            'errors' => $errors,

        ], $status);

    }
}
