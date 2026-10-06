<?php

namespace App\Http\Requests\Career;

use Illuminate\Foundation\Http\FormRequest;

class GenerateCareerRecommendationRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'career_goal' => [
                'nullable',
                'string',
                'max:255',
            ],
        ];
    }
}
