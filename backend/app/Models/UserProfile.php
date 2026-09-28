<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class UserProfile extends Model
{
    protected $fillable = [

        'user_id',

        'first_name',
        'last_name',

        'phone',
        'location',
        'country',

        'headline',
        'summary',

        'linkedin_url',
        'github_url',
        'portfolio_url',

        'years_experience',

    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
