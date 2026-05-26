<?php
namespace Tests\Feature;

use App\Models\AdminAction;
use App\Models\ReportedContent;
use App\Models\SystemSetting;
use Tests\TestCase;

class AdminApiTest extends TestCase
{
    use \Illuminate\Foundation\Testing\RefreshDatabase;

    protected function adminHeaders(): array
    {
        return [
            'X-User-Id' => 'admin-1',
            'X-User-Email' => 'admin@test.com',
            'X-User-Role' => 'ADMIN',
            'Accept' => 'application/json',
        ];
    }

    protected function playerHeaders(): array
    {
        return [
            'X-User-Id' => 'user-1',
            'X-User-Email' => 'user@test.com',
            'X-User-Role' => 'PLAYER',
            'Accept' => 'application/json',
        ];
    }

    protected function setUp(): void
    {
        parent::setUp();
        SystemSetting::create([
            'key' => 'site_name',
            'value' => 'Chess App',
            'description' => 'Site name',
            'type' => 'string',
        ]);
    }

    public function test_dashboard_requires_admin()
    {
        $this->getJson('/api/admin/dashboard', $this->playerHeaders())
            ->assertStatus(403)
            ->assertJsonPath('message', 'Admin access required');
    }

    public function test_dashboard_requires_auth()
    {
        $this->getJson('/api/admin/dashboard', ['Accept' => 'application/json'])
            ->assertStatus(401)
            ->assertJsonPath('message', 'Authentication required');
    }

    public function test_dashboard_returns_stats()
    {
        $this->getJson('/api/admin/dashboard', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonPath('success', true)
            ->assertJsonStructure(['data' => [
                'total_admin_actions', 'unique_admins', 'pending_reports', 'total_settings', 'recent_actions',
            ]]);
    }

    public function test_audit_log_paginated()
    {
        AdminAction::create([
            'admin_id' => 'admin-1',
            'action' => 'test_action',
            'resource_type' => 'test',
            'resource_id' => '123',
        ]);

        $this->getJson('/api/admin/audit-log', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonPath('success', true)
            ->assertJsonStructure(['data', 'meta' => ['current_page', 'per_page', 'total', 'last_page']]);
    }

    public function test_audit_log_filter_by_action()
    {
        AdminAction::create([
            'admin_id' => 'admin-1',
            'action' => 'delete_thread',
            'resource_type' => 'thread',
            'resource_id' => 't1',
        ]);

        $this->getJson('/api/admin/audit-log?action=delete_thread', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonCount(1, 'data');
    }

    public function test_settings_list()
    {
        $this->getJson('/api/admin/settings', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonPath('success', true)
            ->assertJsonPath('data.0.key', 'site_name');
    }

    public function test_settings_get_by_key()
    {
        $this->getJson('/api/admin/settings?key=site_name', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonPath('data.key', 'site_name')
            ->assertJsonPath('data.value', 'Chess App');
    }

    public function test_update_settings()
    {
        $this->putJson('/api/admin/settings', [
            'settings' => [
                ['key' => 'site_name', 'value' => 'New Name', 'description' => 'Updated site name'],
                ['key' => 'maintenance_mode', 'value' => 'false', 'type' => 'boolean'],
            ],
        ], $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonPath('success', true);

        $this->assertDatabaseHas('system_settings', ['key' => 'site_name', 'value' => 'New Name']);
        $this->assertDatabaseHas('system_settings', ['key' => 'maintenance_mode', 'value' => 'false']);
    }

    public function test_update_settings_validation()
    {
        $this->putJson('/api/admin/settings', [
            'settings' => 'invalid',
        ], $this->adminHeaders())
            ->assertStatus(422);
    }

    public function test_reported_content_list()
    {
        ReportedContent::create([
            'reporter_id' => 'user-1',
            'resource_type' => 'thread',
            'resource_id' => 't1',
            'reason' => 'This contains inappropriate content',
            'status' => ReportedContent::STATUS_PENDING,
        ]);

        $this->getJson('/api/admin/reported-content', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonPath('success', true)
            ->assertJsonCount(1, 'data');
    }

    public function test_create_report()
    {
        $this->postJson('/api/admin/reported-content', [
            'resource_type' => 'thread',
            'resource_id' => 't123',
            'reason' => 'This post contains spam and should be reviewed',
        ], $this->adminHeaders())
            ->assertStatus(201)
            ->assertJsonPath('success', true)
            ->assertJsonPath('data.reason', 'This post contains spam and should be reviewed');
    }

    public function test_create_report_duplicate()
    {
        $this->postJson('/api/admin/reported-content', [
            'resource_type' => 'thread',
            'resource_id' => 't1',
            'reason' => 'This post contains spam and should be reviewed',
        ], $this->adminHeaders());

        $this->postJson('/api/admin/reported-content', [
            'resource_type' => 'thread',
            'resource_id' => 't1',
            'reason' => 'Duplicate report of the same content',
        ], $this->adminHeaders())
            ->assertStatus(409);
    }

    public function test_moderate_report()
    {
        $report = ReportedContent::create([
            'reporter_id' => 'user-1',
            'resource_type' => 'post',
            'resource_id' => 'p1',
            'reason' => 'This contains spam links',
            'status' => ReportedContent::STATUS_PENDING,
        ]);

        $this->putJson("/api/admin/reported-content/{$report->id}", [
            'status' => 'ACTION_TAKEN',
            'note' => 'Removed spam content',
        ], $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonPath('data.status', 'ACTION_TAKEN');
    }

    public function test_moderate_report_not_found()
    {
        $this->putJson('/api/admin/reported-content/nonexistent', [
            'status' => 'DISMISSED',
        ], $this->adminHeaders())
            ->assertStatus(404);
    }

    public function test_reported_content_filter_by_status()
    {
        ReportedContent::create([
            'reporter_id' => 'user-1',
            'resource_type' => 'thread',
            'resource_id' => 't1',
            'reason' => 'This needs moderation review immediately',
            'status' => ReportedContent::STATUS_PENDING,
        ]);
        ReportedContent::create([
            'reporter_id' => 'user-2',
            'resource_type' => 'post',
            'resource_id' => 'p1',
            'reason' => 'This was already reviewed and dismissed',
            'status' => ReportedContent::STATUS_DISMISSED,
        ]);

        $this->getJson('/api/admin/reported-content?status=PENDING', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonCount(1, 'data');

        $this->getJson('/api/admin/reported-content?status=DISMISSED', $this->adminHeaders())
            ->assertStatus(200)
            ->assertJsonCount(1, 'data');
    }
}
