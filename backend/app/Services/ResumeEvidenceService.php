<?php

namespace App\Services;

use App\Models\Resume;
use Illuminate\Support\Facades\Http;
use RuntimeException;

class ResumeEvidenceService
{
    private const ANALYSIS_FIELDS = [
        'ats_score',
        'extracted_name',
        'extracted_email',
        'skills',
        'education',
        'experience',
        'summary',
        'status',
    ];

    private const EVIDENCE_FIELDS = [
        'field_path',
        'skill_name',
        'status',
        'review_flags',
    ];

    private const EVIDENCE_STATUSES = [
        'no_literal_evidence',
        'literal_mention_only',
        'explicit_rejection_only',
        'mixed_mentions',
    ];

    private const REVIEW_FLAGS = [
        'aspirational_wording',
        'requirement_wording',
        'rejection_with_contrast',
    ];

    public function __construct(
        private ResumeParserService $parser
    ) {}

    public function generate(Resume $resume): array
    {
        $text = $this->parser->extractText($resume);

        $response = Http::timeout(30)
            ->post(
                config('services.ai_engine.url')
                    .'/analyze/evidence',
                [
                    'resume_text' => $text,
                ]
            );

        if ($response->failed()) {
            throw new RuntimeException(
                'AI Engine evidence request failed'
            );
        }

        $result = $response->json();

        return $this->validateResponse($result);
    }

    private function validateResponse(mixed $result): array
    {
        if (
            ! is_array($result)
            || ! is_array($result['analysis'] ?? null)
            || ! is_array($result['skill_evidence'] ?? null)
            || ! array_is_list($result['skill_evidence'])
        ) {
            throw new RuntimeException(
                'Invalid AI Engine evidence response'
            );
        }

        $analysis = $result['analysis'];

        foreach (self::ANALYSIS_FIELDS as $field) {
            if (! array_key_exists($field, $analysis)) {
                throw new RuntimeException(
                    'Incomplete AI Engine analysis response'
                );
            }
        }

        foreach (['skills', 'education', 'experience'] as $field) {
            if (
                ! is_array($analysis[$field])
                || ! array_is_list($analysis[$field])
            ) {
                throw new RuntimeException(
                    'Invalid AI Engine analysis fields'
                );
            }
        }

        if (! is_string($analysis['status'])) {
            throw new RuntimeException(
                'Invalid AI Engine analysis status'
            );
        }

        $evidence = [];

        foreach ($result['skill_evidence'] as $item) {
            if (! is_array($item)) {
                throw new RuntimeException(
                    'Invalid skill evidence item'
                );
            }

            foreach (self::EVIDENCE_FIELDS as $field) {
                if (! array_key_exists($field, $item)) {
                    throw new RuntimeException(
                        'Incomplete skill evidence item'
                    );
                }
            }

            if (
                ! is_string($item['field_path'])
                || $item['field_path'] === ''
                || ! is_string($item['skill_name'])
                || $item['skill_name'] === ''
                || ! in_array(
                    $item['status'],
                    self::EVIDENCE_STATUSES,
                    true
                )
                || ! is_array($item['review_flags'])
                || ! array_is_list($item['review_flags'])
            ) {
                throw new RuntimeException(
                    'Invalid skill evidence fields'
                );
            }

            foreach ($item['review_flags'] as $flag) {
                if (! in_array(
                    $flag,
                    self::REVIEW_FLAGS,
                    true
                )) {
                    throw new RuntimeException(
                        'Invalid skill evidence review flag'
                    );
                }
            }

            $evidence[] = array_intersect_key(
                $item,
                array_flip(self::EVIDENCE_FIELDS)
            );
        }

        return [
            'analysis' => array_intersect_key(
                $analysis,
                array_flip(self::ANALYSIS_FIELDS)
            ),
            'skill_evidence' => $evidence,
        ];
    }
}
