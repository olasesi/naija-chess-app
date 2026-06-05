<?php
namespace App\Http\Controllers\Api;

use App\Models\AdminAction;
use App\Models\ReportedContent;
use App\Models\SystemSetting;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Validator;


class AdminController
{
    protected function success($data, $message = 'Success', $status = 200, $meta = null)
    {
        $response = ['success' => true, 'message' => $message, 'data' => $data];
        if ($meta) {
            $response['meta'] = $meta;
        }
        return response()->json($response, $status);
    }

    protected function error($message, $status = 400, $errors = null)
    {
        $response = ['success' => false, 'message' => $message];
        if ($errors) {
            $response['errors'] = $errors;
        }
        return response()->json($response, $status);
    }

    protected function logAction(Request $request, string $action, ?string $resourceType = null, ?string $resourceId = null, ?array $details = null)
    {
        AdminAction::create([
            'admin_id' => $request->input('x_user_id'),
            'action' => $action,
            'resource_type' => $resourceType,
            'resource_id' => $resourceId,
            'details' => $details,
            'ip_address' => $request->ip(),
        ]);
    }

    // GET /api/admin/dashboard
    public function dashboard()
    {
        $adminCount = AdminAction::distinct('admin_id')->count('admin_id');
        $reportedPending = ReportedContent::where('status', ReportedContent::STATUS_PENDING)->count();
        $settingsCount = SystemSetting::count();

        return $this->success([
            'total_admin_actions' => AdminAction::count(),
            'unique_admins' => $adminCount,
            'pending_reports' => $reportedPending,
            'total_settings' => $settingsCount,
            'recent_actions' => AdminAction::latest()->take(10)->get(),
        ]);
    }

    // GET /api/admin/audit-log
    public function auditLog(Request $request)
    {
        $query = AdminAction::query();

        if ($request->filled('admin_id')) {
            $query->where('admin_id', $request->input('admin_id'));
        }
        if ($request->filled('action')) {
            $query->where('action', $request->input('action'));
        }
        if ($request->filled('resource_type')) {
            $query->where('resource_type', $request->input('resource_type'));
        }

        $perPage = min((int) $request->input('per_page', 20), 100);
        $actions = $query->orderBy('created_at', 'desc')->paginate($perPage);

        return $this->success(
            $actions->items(),
            'Success',
            200,
            [
                'current_page' => $actions->currentPage(),
                'per_page' => $actions->perPage(),
                'total' => $actions->total(),
                'last_page' => $actions->lastPage(),
            ]
        );
    }

    // GET /api/admin/settings
    public function settings(Request $request)
    {
        if ($request->filled('key')) {
            $setting = SystemSetting::where('key', $request->input('key'))->first();
            if (!$setting) {
                return $this->error('Setting not found', 404);
            }
            return $this->success($setting);
        }

        $perPage = min((int) $request->input('per_page', 50), 200);
        $settings = SystemSetting::orderBy('key')->paginate($perPage);

        return $this->success(
            $settings->items(),
            'Success',
            200,
            [
                'current_page' => $settings->currentPage(),
                'per_page' => $settings->perPage(),
                'total' => $settings->total(),
                'last_page' => $settings->lastPage(),
            ]
        );
    }

    // PUT /api/admin/settings
    public function updateSettings(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'settings' => 'required|array',
            'settings.*.key' => 'required|string',
            'settings.*.value' => 'nullable',
            'settings.*.description' => 'nullable|string',
            'settings.*.type' => 'nullable|string|in:string,boolean,integer,json',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors(),
            ], 422);
        }

        $updated = [];
        foreach ($request->input('settings') as $item) {
            $setting = SystemSetting::updateOrCreate(
                ['key' => $item['key']],
                [
                    'value' => $item['value'] ?? null,
                    'description' => $item['description'] ?? null,
                    'type' => $item['type'] ?? 'string',
                ]
            );
            $updated[] = $setting;
        }

        $this->logAction($request, 'update_settings', 'system_settings', null, [
            'count' => count($updated),
            'keys' => array_column($request->input('settings'), 'key'),
        ]);

        return $this->success($updated, 'Settings updated');
    }

    // GET /api/admin/reported-content
    public function reportedContent(Request $request)
    {
        $query = ReportedContent::query();

        if ($request->filled('status')) {
            $query->where('status', $request->input('status'));
        }
        if ($request->filled('resource_type')) {
            $query->where('resource_type', $request->input('resource_type'));
        }

        $perPage = min((int) $request->input('per_page', 20), 100);
        $reports = $query->orderBy('created_at', 'desc')->paginate($perPage);

        return $this->success(
            $reports->items(),
            'Success',
            200,
            [
                'current_page' => $reports->currentPage(),
                'per_page' => $reports->perPage(),
                'total' => $reports->total(),
                'last_page' => $reports->lastPage(),
            ]
        );
    }

    // POST /api/admin/reported-content
    public function createReport(Request $request)
    {
        $validator = Validator::make($request->all(), [
            'resource_type' => 'required|string',
            'resource_id' => 'required|string',
            'reason' => 'required|string|min:10',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors(),
            ], 422);
        }

        $existing = ReportedContent::where('reporter_id', $request->input('x_user_id'))
            ->where('resource_type', $request->input('resource_type'))
            ->where('resource_id', $request->input('resource_id'))
            ->where('status', ReportedContent::STATUS_PENDING)
            ->first();

        if ($existing) {
            return $this->error('You have already reported this content', 409);
        }

        $report = ReportedContent::create([
            'reporter_id' => $request->input('x_user_id'),
            'resource_type' => $request->input('resource_type'),
            'resource_id' => $request->input('resource_id'),
            'reason' => $request->input('reason'),
            'status' => ReportedContent::STATUS_PENDING,
        ]);

        return $this->success($report, 'Report created', 201);
    }

    // PUT /api/admin/reported-content/{id}
    public function moderateReport(Request $request, string $id)
    {
        $report = ReportedContent::find($id);
        if (!$report) {
            return $this->error('Report not found', 404);
        }

        $validator = Validator::make($request->all(), [
            'status' => 'required|string|in:DISMISSED,ACTION_TAKEN',
            'note' => 'nullable|string',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Validation failed',
                'errors' => $validator->errors(),
            ], 422);
        }

        $report->update([
            'status' => $request->input('status'),
            'moderator_id' => $request->input('x_user_id'),
            'moderated_at' => now(),
        ]);

        $this->logAction($request, 'moderate_report', 'reported_content', $id, [
            'status' => $request->input('status'),
            'note' => $request->input('note'),
        ]);

        return $this->success($report, 'Report moderated');
    }
}
