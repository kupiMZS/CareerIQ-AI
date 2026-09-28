<?php

namespace App\Services;

use App\Models\Resume;
use App\Models\User;
use Illuminate\Http\UploadedFile;

class ResumeService
{
    public function upload(
        User $user,
        array $data,
        UploadedFile $file
    ): Resume {

        $path = $file->store(
            'resumes/'.$user->id
        );

        return $user->resumes()->create([

            'title' => $data['title'],

            'file_name' => $file->getClientOriginalName(),

            'file_path' => $path,

            'file_type' => $file->getMimeType(),

            'file_size' => $file->getSize(),

            'status' => 'uploaded',

        ]);

    }

    public function getUserResumes(User $user)
    {
        return $user->resumes;
    }

    public function delete(Resume $resume): bool
    {
        return $resume->delete();
    }
}
