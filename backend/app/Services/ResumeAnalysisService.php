<?php

namespace App\Services;

use App\Models\Resume;
use App\Models\ResumeAnalysis;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class ResumeAnalysisService
{
    public function __construct(
        private ResumeParserService $parser
    ) {}

    public function createPendingAnalysis(
        Resume $resume
    ): ResumeAnalysis {
        $analysis = ResumeAnalysis::updateOrCreate(
            [
                'resume_id' => $resume->id,
            ],
            [
                'ats_score' => null,
                'extracted_name' => null,
                'extracted_email' => null,
                'skills' => null,
                'education' => null,
                'experience' => null,
                'summary' => null,
                'status' => 'processing',
            ]
        );

        try {
            $text = $this->parser->extractText($resume);

            $response = Http::timeout(30)
                ->post(
                    config('services.ai_engine.url').'/analyze',
                    [
                        'resume_text' => $text,
                    ]
                );

            if ($response->failed()) {
                throw new RuntimeException(
                    'AI Engine returned HTTP '.$response->status()
                );
            }

            $result = $response->json();

            $this->updateAnalysis($analysis, [
                'ats_score' => $result['ats_score'] ?? null,
                'extracted_name' => $result['extracted_name'] ?? null,
                'extracted_email' => $result['extracted_email'] ?? null,
                'skills' => $result['skills'] ?? [],
                'education' => $result['education'] ?? [],
                'experience' => $result['experience'] ?? [],
                'summary' => $result['summary'] ?? null,
                'status' => $result['status'] ?? 'completed',
            ]);
        } catch (\Throwable $exception) {
            $this->updateAnalysis($analysis, [
                'status' => 'failed',
                'summary' => $exception->getMessage(),
            ]);
        }

        return $analysis->refresh();
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
