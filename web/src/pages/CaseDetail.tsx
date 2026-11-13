import { useParams } from 'react-router-dom'
import { Placeholder } from '@/components/Placeholder'

export default function CaseDetail() {
  const { id } = useParams()
  return <Placeholder title={`Case ${id}`} task="Task E5 builds this page." />
}
