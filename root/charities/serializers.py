from rest_framework import serializers
from .models import Benefactor, Charity, Task


class BenefactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefactor
        fields = ['experience', 'free_time_per_week']

    def save(self, **kwargs):
        user = kwargs.get('user')
        if user:
            self.validated_data['user'] = user
        return super().save(**kwargs)


class CharitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Charity
        fields = ['name', 'reg_number']

    def save(self, **kwargs):
        user = kwargs.get('user')
        if user:
            self.validated_data['user'] = user
        return super().save(**kwargs)

class TaskSerializer(serializers.ModelSerializer):
    state = serializers.ChoiceField(read_only=True, choices=Task.TaskStatus.choices)
    assigned_benefactor = BenefactorSerializer(required=False)
    charity = CharitySerializer(read_only=True)
    charity_id = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Charity.objects.all(), source='charity')

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'state',
            'charity',
            'charity_id',
            'description',
            'assigned_benefactor',
            'date',
            'age_limit_from',
            'age_limit_to',
            'gender_limit',
        )
