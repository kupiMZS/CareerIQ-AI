<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Resume extends Model
{
    protected $fillable = [

        'user_id',

        'title',

        'file_name',

        'file_path',

        'file_type',

        'file_size',

        'status',

    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
    public function analysis(): HasOne
    {
        return $this->hasOne(ResumeAnalysis::class);
    }
}

