<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;


class ResumeAnalysisResource extends JsonResource
{

    public function toArray(Request $request): array
    {

        return [

            'id' => $this->id,

            'resume_id' => $this->resume_id,

            'ats_score' => $this->ats_score,

            'extracted_name' => $this->extracted_name,

            'extracted_email' => $this->extracted_email,

            'skills' => $this->skills,

            'education' => $this->education,

            'experience' => $this->experience,

            'summary' => $this->summary,

            'status' => $this->status,

            'created_at' => $this->created_at,

        ];

    }

}
