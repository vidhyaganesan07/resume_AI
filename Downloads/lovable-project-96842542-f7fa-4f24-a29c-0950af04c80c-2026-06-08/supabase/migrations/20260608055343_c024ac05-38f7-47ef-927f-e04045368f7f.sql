
CREATE POLICY user_roles_self_insert_safe ON public.user_roles
  FOR INSERT TO authenticated
  WITH CHECK (auth.uid() = user_id AND role IN ('job_seeker','recruiter'));

CREATE POLICY user_roles_self_delete_safe ON public.user_roles
  FOR DELETE TO authenticated
  USING (auth.uid() = user_id AND role IN ('job_seeker','recruiter'));
