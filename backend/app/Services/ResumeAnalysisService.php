<?php

namespace App\Services;

use App\Models\Resume;
use App\Models\ResumeAnalysis;


class ResumeAnalysisService
{


    public function createPendingAnalysis(
        Resume $resume
    ): ResumeAnalysis {


        return $resume->analysis()->create([

            'status' => 'pending',

        ]);

    }



    public function updateAnalysis(
        ResumeAnalysis $analysis,
        array $data
    ): ResumeAnalysis {


        $analysis->update([

            'ats_score' => $data['ats_score'] ?? null,

            'extracted_name' => $data['extracted_name'] ?? null,

            'extracted_email' => $data['extracted_email'] ?? null,

            'skills' => $data['skills'] ?? null,

            'education' => $data['education'] ?? null,

            'experience' => $data['experience'] ?? null,

            'summary' => $data['summary'] ?? null,

            'status' => $data['status'] ?? 'completed',

        ]);


        return $analysis;

    }



    public function getAnalysis(
        Resume $resume
    ): ?ResumeAnalysis {


        return $resume->analysis;

    }


}
