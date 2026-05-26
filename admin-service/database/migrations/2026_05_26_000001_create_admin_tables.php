<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('system_settings', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('key')->unique();
            $table->text('value')->nullable();
            $table->string('description')->nullable();
            $table->string('type')->default('string');
            $table->timestamps();
        });

        Schema::create('admin_actions', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('admin_id');
            $table->string('action');
            $table->string('resource_type')->nullable();
            $table->string('resource_id')->nullable();
            $table->json('details')->nullable();
            $table->string('ip_address')->nullable();
            $table->timestamps();
            $table->index('admin_id');
        });

        Schema::create('reported_content', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('reporter_id');
            $table->string('resource_type');
            $table->string('resource_id');
            $table->text('reason');
            $table->string('status')->default('PENDING');
            $table->string('moderator_id')->nullable();
            $table->timestamp('moderated_at')->nullable();
            $table->timestamps();
            $table->index('status');
            $table->index('reporter_id');
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('reported_content');
        Schema::dropIfExists('admin_actions');
        Schema::dropIfExists('system_settings');
    }
};
