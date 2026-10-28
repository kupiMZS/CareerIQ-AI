<?php

namespace App\Services;

use App\Models\Resume;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class ResumeAtsService
{
    private const FINDING_CODES = [
        'contact_email',
        'section_skills',
        'section_education',
        'section_experience',
        'section_skills_content',
        'section_education_content',
        'section_experience_content',
        'quantified_outcome_evidence',
    ];

    private const FINDING_STATUSES = [
        'satisfied',
        'needs_attention',
        'not_assessed',
    ];

    private const REPORT_FIELDS = [
        'report_version',
        'score',
        'findings',
        'limitations',
    ];

    private const FINDING_FIELDS = [
        'code',
        'status',
        'explanation',
        'supporting_text',
        'recommendation',
    ];

    public function __construct(
        private ResumeParserService $parser
    ) {}

    public function generate(Resume $resume): array
    {
        $text = $this->parser->extractText($resume);

        $response = Http::timeout(30)
            ->post(
                config('services.ai_engine.url').'/analyze/ats',
                [
                    'resume_text' => $text,
                ]
            );

        if ($response->failed()) {
            throw new RuntimeException(
                'AI Engine ATS request failed'
            );
        }

        return $this->validateResponse($response->json());
    }

    private function hasExactKeys(
        array $value,
        array $expected
    ): bool {
        return count($value) === count($expected)
            && array_diff(array_keys($value), $expected) === [];
    }

    private function validateResponse(mixed $result): array
    {
        if (
            ! is_array($result)
            || ! $this->hasExactKeys(
                $result,
                self::REPORT_FIELDS
            )
            || ($result['report_version'] ?? null) !== 'ats-v1'
            || ! array_key_exists('score', $result)
            || $result['score'] !== null
            || ! is_array($result['findings'])
            || ! array_is_list($result['findings'])
            || count($result['findings'])
                !== count(self::FINDING_CODES)
            || ! is_array($result['limitations'])
            || ! array_is_list($result['limitations'])
        ) {
            throw new RuntimeException(
                'Invalid AI Engine ATS response'
            );
        }

        foreach ($result['findings'] as $index => $finding) {
            if (
                ! is_array($finding)
                || ! $this->hasExactKeys(
                    $finding,
                    self::FINDING_FIELDS
                )
                || $finding['code']
                    !== self::FINDING_CODES[$index]
                || ! in_array(
                    $finding['status'],
                    self::FINDING_STATUSES,
                    true
                )
                || ! is_string($finding['explanation'])
                || trim($finding['explanation']) === ''
                || ! is_array($finding['supporting_text'])
                || ! array_is_list($finding['supporting_text'])
                || (
                    $finding['recommendation'] !== null
                    && ! is_string($finding['recommendation'])
                )
            ) {
                throw new RuntimeException(
                    'Invalid AI Engine ATS finding'
                );
            }

            foreach ($finding['supporting_text'] as $excerpt) {
                if (! is_string($excerpt)) {
                    throw new RuntimeException(
                        'Invalid AI Engine ATS supporting text'
                    );
                }
            }
        }

        foreach ($result['limitations'] as $limitation) {
            if (
                ! is_string($limitation)
                || trim($limitation) === ''
            ) {
                throw new RuntimeException(
                    'Invalid AI Engine ATS limitation'
                );
            }
        }

        return $result;
    }
}
