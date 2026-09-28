<?php

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class ResumeResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [

            'id' => $this->id,

            'title' => $this->title,

            'file_name' => $this->file_name,

            'file_path' => $this->file_path,

            'file_type' => $this->file_type,

            'file_size' => $this->file_size,

            'status' => $this->status,

            'created_at' => $this->created_at,

        ];
    }
}
