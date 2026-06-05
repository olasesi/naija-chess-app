import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

// ── Example schema ──────────────────────────────────────────────────────────
export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

// ── Reusable typed form factory ─────────────────────────────────────────────
export function useValidatedForm<T extends z.ZodType>(
  schema: T,
  defaultValues?: Partial<z.infer<T>>,
) {
  return useForm<z.infer<T>>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues as z.infer<T>,
    mode: 'onTouched',
  });
}

// ── Usage in a screen ───────────────────────────────────────────────────────
// const { control, handleSubmit, formState: { errors } } = useValidatedForm(loginSchema);
