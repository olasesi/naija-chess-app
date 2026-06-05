<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;

class ReportedContent extends Model
{
    use HasUuids;

    const STATUS_PENDING = 'PENDING';
    const STATUS_DISMISSED = 'DISMISSED';
    const STATUS_ACTION_TAKEN = 'ACTION_TAKEN';

    protected $table = 'reported_content';

    protected $fillable = [
        'reporter_id', 'resource_type', 'resource_id', 'reason',
        'status', 'moderator_id', 'moderated_at'
    ];

    public $incrementing = false;
    protected $keyType = 'string';

    protected function casts(): array
    {
        return ['moderated_at' => 'datetime'];
    }
}
