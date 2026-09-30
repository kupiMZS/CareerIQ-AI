<?php

namespace App\Services;

use App\Models\Resume;
use Smalot\PdfParser\Parser;

class ResumeParserService
{
    public function extractText(
        Resume $resume
    ): string {

        $filePath = storage_path(
            'app/private/'.$resume->file_path
        );

        if (! file_exists($filePath)) {

            throw new \Exception(
                'Resume file not found'
            );

        }

        $parser = new Parser;

        $pdf = $parser->parseFile($filePath);

        return trim(
            $pdf->getText()
        );

    }
}
