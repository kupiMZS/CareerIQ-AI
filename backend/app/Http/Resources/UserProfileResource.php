<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class UserProfileResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [

            'id' => $this->id,

            'first_name' => $this->first_name,

            'last_name' => $this->last_name,

            'phone' => $this->phone,

            'location' => $this->location,

            'country' => $this->country,

            'headline' => $this->headline,

            'summary' => $this->summary,

            'linkedin_url' => $this->linkedin_url,

            'github_url' => $this->github_url,

            'portfolio_url' => $this->portfolio_url,

            'years_experience' => $this->years_experience,

        ];
    }
}
