import AdvisorLayout from '@/components/advisor/AdvisorLayout';

export default function AdvisorRouteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AdvisorLayout>{children}</AdvisorLayout>;
}
