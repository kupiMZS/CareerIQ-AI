<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Http\Requests\Resume\StoreResumeRequest;
use App\Http\Resources\ResumeResource;
use App\Services\ResumeService;
use Illuminate\Http\Request;

class ResumeController extends Controller
{
    public function __construct(
        private ResumeService $resumeService
    ) {}

    public function store(
        StoreResumeRequest $request
    ) {

        $resume = $this->resumeService->upload(

            $request->user(),

            $request->validated(),

            $request->file('file')

        );

        return response()->json([

            'message' => 'Resume uploaded successfully',

            'data' => new ResumeResource($resume),

        ], 201);

    }

    public function index(Request $request)
    {

        return ResumeResource::collection(

            $this->resumeService
                ->getUserResumes($request->user())

        );

    }

    public function destroy(
        Request $request,
        int $id
    ) {

        $resume = $request->user()
            ->resumes()
            ->findOrFail($id);

        $this->resumeService->delete($resume);

        return response()->json([

            'message' => 'Resume deleted successfully',

        ]);

    }
}
