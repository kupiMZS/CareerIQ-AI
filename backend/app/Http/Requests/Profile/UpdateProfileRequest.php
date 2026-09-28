<?php

namespace App\Http\Requests\Profile;

use Illuminate\Foundation\Http\FormRequest;

class UpdateProfileRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [

            'first_name' => [
                'sometimes',
                'nullable',
                'string',
                'max:100',
            ],

            'last_name' => [
                'sometimes',
                'nullable',
                'string',
                'max:100',
            ],

            'phone' => [
                'sometimes',
                'nullable',
                'string',
                'max:30',
            ],

            'location' => [
                'sometimes',
                'nullable',
                'string',
                'max:100',
            ],

            'country' => [
                'sometimes',
                'nullable',
                'string',
                'max:100',
            ],

            'headline' => [
                'sometimes',
                'nullable',
                'string',
                'max:255',
            ],

            'summary' => [
                'sometimes',
                'nullable',
                'string',
                'max:2000',
            ],

            'linkedin_url' => [
                'sometimes',
                'nullable',
                'url',
                'max:255',
            ],

            'github_url' => [
                'sometimes',
                'nullable',
                'url',
                'max:255',
            ],

            'portfolio_url' => [
                'sometimes',
                'nullable',
                'url',
                'max:255',
            ],

            'years_experience' => [
                'sometimes',
                'nullable',
                'integer',
                'min:0',
                'max:80',
            ],

        ];
    }
}
