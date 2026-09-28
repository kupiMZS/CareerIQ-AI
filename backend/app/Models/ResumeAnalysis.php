<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;


class ResumeAnalysis extends Model
{

    protected $fillable = [

        'resume_id',

        'ats_score',

        'extracted_name',

        'extracted_email',

        'skills',

        'education',

        'experience',

        'summary',

        'status',

    ];



    protected $casts = [

        'skills' => 'array',

        'education' => 'array',

        'experience' => 'array',

    ];



    public function resume(): BelongsTo
    {
        return $this->belongsTo(Resume::class);
    }

}
